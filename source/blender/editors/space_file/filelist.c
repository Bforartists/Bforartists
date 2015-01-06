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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_file/filelist.c
 *  \ingroup spfile
 */


/* global includes */

#include <stdlib.h>
#include <math.h>
#include <string.h>

#ifndef WIN32
#include <unistd.h>
#else
#include <io.h>
#include <direct.h>
#endif   
#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_fileops_types.h"
#include "BLI_fnmatch.h"
#include "BLI_linklist.h"
#include "BLI_utildefines.h"

#ifdef WIN32
#  include "BLI_winstuff.h"
#endif

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_icons.h"
#include "BKE_main.h"
#include "BKE_report.h"
#include "BLO_readfile.h"
#include "BKE_idcode.h"

#include "DNA_space_types.h"

#include "ED_datafiles.h"
#include "ED_fileselect.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"
#include "IMB_thumbs.h"

#include "PIL_time.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_resources.h"

#include "filelist.h"


/* ----------------- FOLDERLIST (previous/next) -------------- */

typedef struct FolderList {
	struct FolderList *next, *prev;
	char *foldername;
} FolderList;

ListBase *folderlist_new(void)
{
	ListBase *p = MEM_callocN(sizeof(ListBase), "folderlist");
	return p;
}

void folderlist_popdir(struct ListBase *folderlist, char *dir)
{
	const char *prev_dir;
	struct FolderList *folder;
	folder = folderlist->last;

	if (folder) {
		/* remove the current directory */
		MEM_freeN(folder->foldername);
		BLI_freelinkN(folderlist, folder);

		folder = folderlist->last;
		if (folder) {
			prev_dir = folder->foldername;
			BLI_strncpy(dir, prev_dir, FILE_MAXDIR);
		}
	}
	/* delete the folder next or use setdir directly before PREVIOUS OP */
}

void folderlist_pushdir(ListBase *folderlist, const char *dir)
{
	struct FolderList *folder, *previous_folder;
	previous_folder = folderlist->last;

	/* check if already exists */
	if (previous_folder && previous_folder->foldername) {
		if (BLI_path_cmp(previous_folder->foldername, dir) == 0) {
			return;
		}
	}

	/* create next folder element */
	folder = (FolderList *)MEM_mallocN(sizeof(FolderList), "FolderList");
	folder->foldername = BLI_strdup(dir);

	/* add it to the end of the list */
	BLI_addtail(folderlist, folder);
}

const char *folderlist_peeklastdir(ListBase *folderlist)
{
	struct FolderList *folder;

	if (!folderlist->last)
		return NULL;

	folder = folderlist->last;
	return folder->foldername;
}

int folderlist_clear_next(struct SpaceFile *sfile)
{
	struct FolderList *folder;

	/* if there is no folder_next there is nothing we can clear */
	if (!sfile->folders_next)
		return 0;

	/* if previous_folder, next_folder or refresh_folder operators are executed it doesn't clear folder_next */
	folder = sfile->folders_prev->last;
	if ((!folder) || (BLI_path_cmp(folder->foldername, sfile->params->dir) == 0))
		return 0;

	/* eventually clear flist->folders_next */
	return 1;
}

/* not listbase itself */
void folderlist_free(ListBase *folderlist)
{
	if (folderlist) {
		FolderList *folder;
		for (folder = folderlist->first; folder; folder = folder->next)
			MEM_freeN(folder->foldername);
		BLI_freelistN(folderlist);
	}
}

ListBase *folderlist_duplicate(ListBase *folderlist)
{
	
	if (folderlist) {
		ListBase *folderlistn = MEM_callocN(sizeof(ListBase), "copy folderlist");
		FolderList *folder;
		
		BLI_duplicatelist(folderlistn, folderlist);
		
		for (folder = folderlistn->first; folder; folder = folder->next) {
			folder->foldername = MEM_dupallocN(folder->foldername);
		}
		return folderlistn;
	}
	return NULL;
}


/* ------------------FILELIST------------------------ */

struct FileList;

typedef struct FileImage {
	struct FileImage *next, *prev;
	char path[FILE_MAX];
	unsigned int flags;
	int index;
	short done;
	ImBuf *img;
} FileImage;

typedef struct FileListFilter {
	bool hide_dot;
	bool hide_parent;
	unsigned int filter;
	char filter_glob[64];
	char filter_search[66];  /* + 2 for heading/trailing implicit '*' wildcards. */
} FileListFilter;

typedef struct FileList {
	struct direntry *filelist;
	int numfiles;
	char dir[FILE_MAX];
	short prv_w;
	short prv_h;

	bool changed;

	short sort;
	bool need_sorting;

	FileListFilter filter_data;
	int *fidx;  /* Also used to detect when we need to filter! */
	int numfiltered;

	bool need_thumbnails;

	struct BlendHandle *libfiledata;

	void (*readf)(struct FileList *);
	bool (*filterf)(struct direntry *, const char *, FileListFilter *);
} FileList;

#define FILENAME_IS_BREADCRUMBS(_n) \
	((_n)[0] == '.' && ((_n)[1] == '\0' || ((_n)[1] == '.' && (_n)[2] == '\0')))

#define SPECIAL_IMG_SIZE 48
#define SPECIAL_IMG_ROWS 4
#define SPECIAL_IMG_COLS 4

enum {
	SPECIAL_IMG_FOLDER      = 0,
	SPECIAL_IMG_PARENT      = 1,
	SPECIAL_IMG_REFRESH     = 2,
	SPECIAL_IMG_BLENDFILE   = 3,
	SPECIAL_IMG_SOUNDFILE   = 4,
	SPECIAL_IMG_MOVIEFILE   = 5,
	SPECIAL_IMG_PYTHONFILE  = 6,
	SPECIAL_IMG_TEXTFILE    = 7,
	SPECIAL_IMG_FONTFILE    = 8,
	SPECIAL_IMG_UNKNOWNFILE = 9,
	SPECIAL_IMG_LOADING     = 10,
	SPECIAL_IMG_BACKUP      = 11,
	SPECIAL_IMG_MAX
};

static ImBuf *gSpecialFileImages[SPECIAL_IMG_MAX];


static void filelist_from_main(struct FileList *filelist);
static void filelist_from_library(struct FileList *filelist);

static void filelist_read_main(struct FileList *filelist);
static void filelist_read_library(struct FileList *filelist);
static void filelist_read_dir(struct FileList *filelist);

static void filelist_filter_clear(FileList *filelist);

/* ********** Sort helpers ********** */

static bool compare_is_directory(const struct direntry *entry)
{
	/* for library browse .blend files may be treated as directories, but
	 * for sorting purposes they should be considered regular files */
	if (S_ISDIR(entry->type))
		return !(entry->flags & (FILE_TYPE_BLENDER | FILE_TYPE_BLENDER_BACKUP));
	
	return false;
}

static int compare_name(const void *a1, const void *a2)
{
	const struct direntry *entry1 = a1, *entry2 = a2;

	/* type is equal to stat.st_mode */

	if (compare_is_directory(entry1)) {
		if (compare_is_directory(entry2) == 0) return (-1);
	}
	else {
		if (compare_is_directory(entry2)) return (1);
	}
	if (S_ISREG(entry1->type)) {
		if (S_ISREG(entry2->type) == 0) return (-1);
	}
	else {
		if (S_ISREG(entry2->type)) return (1);
	}
	if ((entry1->type & S_IFMT) < (entry2->type & S_IFMT)) return (-1);
	if ((entry1->type & S_IFMT) > (entry2->type & S_IFMT)) return (1);
	
	/* make sure "." and ".." are always first */
	if (strcmp(entry1->relname, ".") == 0) return (-1);
	if (strcmp(entry2->relname, ".") == 0) return (1);
	if (strcmp(entry1->relname, "..") == 0) return (-1);
	if (strcmp(entry2->relname, "..") == 0) return (1);
	
	return (BLI_natstrcmp(entry1->relname, entry2->relname));
}

static int compare_date(const void *a1, const void *a2)	
{
	const struct direntry *entry1 = a1, *entry2 = a2;
	
	/* type is equal to stat.st_mode */

	if (compare_is_directory(entry1)) {
		if (compare_is_directory(entry2) == 0) return (-1);
	}
	else {
		if (compare_is_directory(entry2)) return (1);
	}
	if (S_ISREG(entry1->type)) {
		if (S_ISREG(entry2->type) == 0) return (-1);
	}
	else {
		if (S_ISREG(entry2->type)) return (1);
	}
	if ((entry1->type & S_IFMT) < (entry2->type & S_IFMT)) return (-1);
	if ((entry1->type & S_IFMT) > (entry2->type & S_IFMT)) return (1);

	/* make sure "." and ".." are always first */
	if (strcmp(entry1->relname, ".") == 0) return (-1);
	if (strcmp(entry2->relname, ".") == 0) return (1);
	if (strcmp(entry1->relname, "..") == 0) return (-1);
	if (strcmp(entry2->relname, "..") == 0) return (1);
	
	if (entry1->s.st_mtime < entry2->s.st_mtime) return 1;
	if (entry1->s.st_mtime > entry2->s.st_mtime) return -1;
	
	else return BLI_natstrcmp(entry1->relname, entry2->relname);
}

static int compare_size(const void *a1, const void *a2)	
{
	const struct direntry *entry1 = a1, *entry2 = a2;

	/* type is equal to stat.st_mode */

	if (compare_is_directory(entry1)) {
		if (compare_is_directory(entry2) == 0) return (-1);
	}
	else {
		if (compare_is_directory(entry2)) return (1);
	}
	if (S_ISREG(entry1->type)) {
		if (S_ISREG(entry2->type) == 0) return (-1);
	}
	else {
		if (S_ISREG(entry2->type)) return (1);
	}
	if ((entry1->type & S_IFMT) < (entry2->type & S_IFMT)) return (-1);
	if ((entry1->type & S_IFMT) > (entry2->type & S_IFMT)) return (1);

	/* make sure "." and ".." are always first */
	if (strcmp(entry1->relname, ".") == 0) return (-1);
	if (strcmp(entry2->relname, ".") == 0) return (1);
	if (strcmp(entry1->relname, "..") == 0) return (-1);
	if (strcmp(entry2->relname, "..") == 0) return (1);
	
	if (entry1->s.st_size < entry2->s.st_size) return 1;
	if (entry1->s.st_size > entry2->s.st_size) return -1;
	else return BLI_natstrcmp(entry1->relname, entry2->relname);
}

static int compare_extension(const void *a1, const void *a2)
{
	const struct direntry *entry1 = a1, *entry2 = a2;
	const char *sufix1, *sufix2;
	const char *nil = "";

	if (!(sufix1 = strstr(entry1->relname, ".blend.gz")))
		sufix1 = strrchr(entry1->relname, '.');
	if (!(sufix2 = strstr(entry2->relname, ".blend.gz")))
		sufix2 = strrchr(entry2->relname, '.');
	if (!sufix1) sufix1 = nil;
	if (!sufix2) sufix2 = nil;

	/* type is equal to stat.st_mode */

	if (compare_is_directory(entry1)) {
		if (compare_is_directory(entry2) == 0) return (-1);
	}
	else {
		if (compare_is_directory(entry2)) return (1);
	}
	if (S_ISREG(entry1->type)) {
		if (S_ISREG(entry2->type) == 0) return (-1);
	}
	else {
		if (S_ISREG(entry2->type)) return (1);
	}
	if ((entry1->type & S_IFMT) < (entry2->type & S_IFMT)) return (-1);
	if ((entry1->type & S_IFMT) > (entry2->type & S_IFMT)) return (1);
	
	/* make sure "." and ".." are always first */
	if (strcmp(entry1->relname, ".") == 0) return (-1);
	if (strcmp(entry2->relname, ".") == 0) return (1);
	if (strcmp(entry1->relname, "..") == 0) return (-1);
	if (strcmp(entry2->relname, "..") == 0) return (1);
	
	return (BLI_strcasecmp(sufix1, sufix2));
}

bool filelist_need_sorting(struct FileList *filelist)
{
	return filelist->need_sorting && (filelist->sort != FILE_SORT_NONE);
}

void filelist_sort(struct FileList *filelist)
{
	if (filelist_need_sorting(filelist)) {
		filelist->need_sorting = false;

		switch (filelist->sort) {
			case FILE_SORT_ALPHA:
				qsort(filelist->filelist, filelist->numfiles, sizeof(struct direntry), compare_name);
				break;
			case FILE_SORT_TIME:
				qsort(filelist->filelist, filelist->numfiles, sizeof(struct direntry), compare_date);
				break;
			case FILE_SORT_SIZE:
				qsort(filelist->filelist, filelist->numfiles, sizeof(struct direntry), compare_size);
				break;
			case FILE_SORT_EXTENSION:
				qsort(filelist->filelist, filelist->numfiles, sizeof(struct direntry), compare_extension);
				break;
			case FILE_SORT_NONE:  /* Should never reach this point! */
			default:
				BLI_assert(0);
				return;
		}

		filelist_filter_clear(filelist);
	}
}

void filelist_setsorting(struct FileList *filelist, const short sort)
{
	if (filelist->sort != sort) {
		filelist->sort = sort;
		filelist->need_sorting = true;
	}
}

/* ********** Filter helpers ********** */

static bool is_hidden_file(const char *filename, FileListFilter *filter)
{
	bool is_hidden = false;

	if (filter->hide_dot) {
		if (filename[0] == '.' && filename[1] != '.' && filename[1] != '\0') {
			is_hidden = true; /* ignore .file */
		}
		else {
			int len = strlen(filename);
			if ((len > 0) && (filename[len - 1] == '~')) {
				is_hidden = true;  /* ignore file~ */
			}
		}
	}
	if (!is_hidden && filter->hide_parent) {
		if (filename[0] == '.' && filename[1] == '.' && filename[2] == '\0') {
			is_hidden = true; /* ignore .. */
		}
	}
	if (!is_hidden && ((filename[0] == '.') && (filename[1] == '\0'))) {
		is_hidden = true; /* ignore . */
	}
	return is_hidden;
}

static bool is_filtered_file(struct direntry *file, const char *UNUSED(root), FileListFilter *filter)
{
	bool is_filtered = !is_hidden_file(file->relname, filter);

	if (is_filtered && filter->filter && !FILENAME_IS_BREADCRUMBS(file->relname)) {
		if ((file->type & S_IFDIR) && !(filter->filter & FILE_TYPE_FOLDER)) {
			is_filtered = false;
		}
		if (!(file->type & S_IFDIR) && !(file->flags & filter->filter)) {
			is_filtered = false;
		}
		if (is_filtered && (filter->filter_search[0] != '\0')) {
			if (fnmatch(filter->filter_search, file->relname, FNM_CASEFOLD) != 0) {
				is_filtered = false;
			}
		}
	}

	return is_filtered;
}

static bool is_filtered_lib(struct direntry *file, const char *root, FileListFilter *filter)
{
	bool is_filtered = !is_hidden_file(file->relname, filter);
	char dir[FILE_MAXDIR], group[BLO_GROUP_MAX];

	if (BLO_is_a_library(root, dir, group)) {
		is_filtered = !is_hidden_file(file->relname, filter);
		if (is_filtered && filter->filter && !FILENAME_IS_BREADCRUMBS(file->relname)) {
			if (is_filtered && (filter->filter_search[0] != '\0')) {
				if (fnmatch(filter->filter_search, file->relname, FNM_CASEFOLD) != 0) {
					is_filtered = false;
				}
			}
		}
	}
	else {
		is_filtered = is_filtered_file(file, root, filter);
	}

	return is_filtered;
}

static bool is_filtered_main(struct direntry *file, const char *UNUSED(dir), FileListFilter *filter)
{
	return !is_hidden_file(file->relname, filter);
}

static void filelist_filter_clear(FileList *filelist)
{
	MEM_SAFE_FREE(filelist->fidx);
	filelist->numfiltered = 0;
}

void filelist_filter(FileList *filelist)
{
	int num_filtered = 0;
	int *fidx_tmp;
	int i;

	if (!filelist->filelist) {
		return;
	}

	if (filelist->fidx) {
		/* Assume it has already been filtered, nothing else to do! */
		return;
	}

	fidx_tmp = MEM_mallocN(sizeof(*fidx_tmp) * (size_t)filelist->numfiles, __func__);

	/* Filter remap & count how many files are left after filter in a single loop. */
	for (i = 0; i < filelist->numfiles; ++i) {
		struct direntry *file = &filelist->filelist[i];

		if (filelist->filterf(file, filelist->dir, &filelist->filter_data)) {
			fidx_tmp[num_filtered++] = i;
		}
	}

	/* Note: maybe we could even accept filelist->fidx to be filelist->numfiles -len allocated? */
	filelist->fidx = (int *)MEM_mallocN(sizeof(*filelist->fidx) * (size_t)num_filtered, __func__);
	memcpy(filelist->fidx, fidx_tmp, sizeof(*filelist->fidx) * (size_t)num_filtered);
	filelist->numfiltered = num_filtered;

	MEM_freeN(fidx_tmp);
}

void filelist_setfilter_options(FileList *filelist, const bool hide_dot, const bool hide_parent,
                                const unsigned int filter,
                                const char *filter_glob, const char *filter_search)
{
	if ((filelist->filter_data.hide_dot != hide_dot) ||
	    (filelist->filter_data.hide_parent != hide_parent) ||
	    (filelist->filter_data.filter != filter) ||
	    !STREQ(filelist->filter_data.filter_glob, filter_glob) ||
	    (BLI_strcmp_ignore_pad(filelist->filter_data.filter_search, filter_search, '*') != 0))
	{
		filelist->filter_data.hide_dot = hide_dot;
		filelist->filter_data.hide_parent = hide_parent;

		filelist->filter_data.filter = filter;
		BLI_strncpy(filelist->filter_data.filter_glob, filter_glob, sizeof(filelist->filter_data.filter_glob));
		BLI_strncpy_ensure_pad(filelist->filter_data.filter_search, filter_search, '*',
		                       sizeof(filelist->filter_data.filter_search));

		/* And now, free filtered data so that we now we have to filter again. */
		filelist_filter_clear(filelist);
	}
}

/* ********** Icon/image helpers ********** */

void filelist_init_icons(void)
{
	short x, y, k;
	ImBuf *bbuf;
	ImBuf *ibuf;

	BLI_assert(G.background == false);

#ifdef WITH_HEADLESS
	bbuf = NULL;
#else
	bbuf = IMB_ibImageFromMemory((unsigned char *)datatoc_prvicons_png, datatoc_prvicons_png_size, IB_rect, NULL, "<splash>");
#endif
	if (bbuf) {
		for (y = 0; y < SPECIAL_IMG_ROWS; y++) {
			for (x = 0; x < SPECIAL_IMG_COLS; x++) {
				int tile = SPECIAL_IMG_COLS * y + x;
				if (tile < SPECIAL_IMG_MAX) {
					ibuf = IMB_allocImBuf(SPECIAL_IMG_SIZE, SPECIAL_IMG_SIZE, 32, IB_rect);
					for (k = 0; k < SPECIAL_IMG_SIZE; k++) {
						memcpy(&ibuf->rect[k * SPECIAL_IMG_SIZE], &bbuf->rect[(k + y * SPECIAL_IMG_SIZE) * SPECIAL_IMG_SIZE * SPECIAL_IMG_COLS + x * SPECIAL_IMG_SIZE], SPECIAL_IMG_SIZE * sizeof(int));
					}
					gSpecialFileImages[tile] = ibuf;
				}
			}
		}
		IMB_freeImBuf(bbuf);
	}
}

void filelist_free_icons(void)
{
	int i;

	BLI_assert(G.background == false);

	for (i = 0; i < SPECIAL_IMG_MAX; ++i) {
		IMB_freeImBuf(gSpecialFileImages[i]);
		gSpecialFileImages[i] = NULL;
	}
}

void filelist_imgsize(struct FileList *filelist, short w, short h)
{
	filelist->prv_w = w;
	filelist->prv_h = h;
}

ImBuf *filelist_getimage(struct FileList *filelist, const int index)
{
	ImBuf *ibuf = NULL;
	int fidx = 0;

	BLI_assert(G.background == false);

	if ((index < 0) || (index >= filelist->numfiltered)) {
		return NULL;
	}
	fidx = filelist->fidx[index];
	ibuf = filelist->filelist[fidx].image;

	return ibuf;
}

ImBuf *filelist_geticon(struct FileList *filelist, const int index)
{
	ImBuf *ibuf = NULL;
	struct direntry *file = NULL;
	int fidx = 0;

	BLI_assert(G.background == false);

	if ((index < 0) || (index >= filelist->numfiltered)) {
		return NULL;
	}
	fidx = filelist->fidx[index];
	file = &filelist->filelist[fidx];
	if (file->type & S_IFDIR) {
		if (strcmp(filelist->filelist[fidx].relname, "..") == 0) {
			ibuf = gSpecialFileImages[SPECIAL_IMG_PARENT];
		}
		else if (strcmp(filelist->filelist[fidx].relname, ".") == 0) {
			ibuf = gSpecialFileImages[SPECIAL_IMG_REFRESH];
		}
		else {
			ibuf = gSpecialFileImages[SPECIAL_IMG_FOLDER];
		}
	}
	else {
		ibuf = gSpecialFileImages[SPECIAL_IMG_UNKNOWNFILE];
	}

	if (file->flags & FILE_TYPE_BLENDER) {
		ibuf = gSpecialFileImages[SPECIAL_IMG_BLENDFILE];
	}
	else if ((file->flags & FILE_TYPE_MOVIE) || (file->flags & FILE_TYPE_MOVIE_ICON)) {
		ibuf = gSpecialFileImages[SPECIAL_IMG_MOVIEFILE];
	}
	else if (file->flags & FILE_TYPE_SOUND) {
		ibuf = gSpecialFileImages[SPECIAL_IMG_SOUNDFILE];
	}
	else if (file->flags & FILE_TYPE_PYSCRIPT) {
		ibuf = gSpecialFileImages[SPECIAL_IMG_PYTHONFILE];
	}
	else if (file->flags & FILE_TYPE_FTFONT) {
		ibuf = gSpecialFileImages[SPECIAL_IMG_FONTFILE];
	}
	else if (file->flags & FILE_TYPE_TEXT) {
		ibuf = gSpecialFileImages[SPECIAL_IMG_TEXTFILE];
	}
	else if (file->flags & FILE_TYPE_IMAGE) {
		ibuf = gSpecialFileImages[SPECIAL_IMG_LOADING];
	}
	else if (file->flags & FILE_TYPE_BLENDER_BACKUP) {
		ibuf = gSpecialFileImages[SPECIAL_IMG_BACKUP];
	}

	return ibuf;
}

/* ********** Main ********** */

FileList *filelist_new(short type)
{
	FileList *p = MEM_callocN(sizeof(FileList), "filelist");
	switch (type) {
		case FILE_MAIN:
			p->readf = filelist_read_main;
			p->filterf = is_filtered_main;
			break;
		case FILE_LOADLIB:
			p->readf = filelist_read_library;
			p->filterf = is_filtered_lib;
			break;
		default:
			p->readf = filelist_read_dir;
			p->filterf = is_filtered_file;
			break;

	}
	return p;
}

void filelist_free(struct FileList *filelist)
{
	if (!filelist) {
		printf("Attempting to delete empty filelist.\n");
		return;
	}
	
	MEM_SAFE_FREE(filelist->fidx);
	filelist->numfiltered = 0;
	memset(&filelist->filter_data, 0, sizeof(filelist->filter_data));

	filelist->need_sorting = false;
	filelist->sort = FILE_SORT_NONE;

	BLI_filelist_free(filelist->filelist, filelist->numfiles, NULL);
	filelist->numfiles = 0;
	filelist->filelist = NULL;
}

void filelist_freelib(struct FileList *filelist)
{
	if (filelist->libfiledata)
		BLO_blendhandle_close(filelist->libfiledata);
	filelist->libfiledata = NULL;
}

BlendHandle *filelist_lib(struct FileList *filelist)
{
	return filelist->libfiledata;
}

int filelist_numfiles(struct FileList *filelist)
{
	return filelist->numfiltered;
}

const char *filelist_dir(struct FileList *filelist)
{
	return filelist->dir;
}

void filelist_setdir(struct FileList *filelist, const char *dir)
{
	BLI_strncpy(filelist->dir, dir, sizeof(filelist->dir));
}

short filelist_changed(struct FileList *filelist)
{
	return filelist->changed;
}

struct direntry *filelist_file(struct FileList *filelist, int index)
{
	int fidx = 0;
	
	if ((index < 0) || (index >= filelist->numfiltered)) {
		return NULL;
	}
	fidx = filelist->fidx[index];

	return &filelist->filelist[fidx];
}

int filelist_find(struct FileList *filelist, const char *filename)
{
	int index = -1;
	int i;
	int fidx = -1;
	
	if (!filelist->fidx) 
		return fidx;

	
	for (i = 0; i < filelist->numfiles; ++i) {
		if (strcmp(filelist->filelist[i].relname, filename) == 0) {  /* not dealing with user input so don't need BLI_path_cmp */
			index = i;
			break;
		}
	}

	for (i = 0; i < filelist->numfiltered; ++i) {
		if (filelist->fidx[i] == index) {
			fidx = i;
			break;
		}
	}
	return fidx;
}

/* would recognize .blend as well */
static bool file_is_blend_backup(const char *str)
{
	const size_t a = strlen(str);
	size_t b = 7;
	bool retval = 0;

	if (a == 0 || b >= a) {
		/* pass */
	}
	else {
		const char *loc;
		
		if (a > b + 1)
			b++;
		
		/* allow .blend1 .blend2 .blend32 */
		loc = BLI_strcasestr(str + a - b, ".blend");
		
		if (loc)
			retval = 1;
	}
	
	return (retval);
}

static int path_extension_type(const char *path)
{
	if (BLO_has_bfile_extension(path)) {
		return FILE_TYPE_BLENDER;
	}
	else if (file_is_blend_backup(path)) {
		return FILE_TYPE_BLENDER_BACKUP;
	}
	else if (BLI_testextensie(path, ".app")) {
		return FILE_TYPE_APPLICATIONBUNDLE;
	}
	else if (BLI_testextensie(path, ".py")) {
		return FILE_TYPE_PYSCRIPT;
	}
	else if (BLI_testextensie_n(path, ".txt", ".glsl", ".osl", ".data", NULL)) {
		return FILE_TYPE_TEXT;
	}
	else if (BLI_testextensie_n(path, ".ttf", ".ttc", ".pfb", ".otf", ".otc", NULL)) {
		return FILE_TYPE_FTFONT;
	}
	else if (BLI_testextensie(path, ".btx")) {
		return FILE_TYPE_BTX;
	}
	else if (BLI_testextensie(path, ".dae")) {
		return FILE_TYPE_COLLADA;
	}
	else if (BLI_testextensie_array(path, imb_ext_image) ||
	         (G.have_quicktime && BLI_testextensie_array(path, imb_ext_image_qt)))
	{
		return FILE_TYPE_IMAGE;
	}
	else if (BLI_testextensie(path, ".ogg")) {
		if (IMB_isanim(path)) {
			return FILE_TYPE_MOVIE;
		}
		else {
			return FILE_TYPE_SOUND;
		}
	}
	else if (BLI_testextensie_array(path, imb_ext_movie)) {
		return FILE_TYPE_MOVIE;
	}
	else if (BLI_testextensie_array(path, imb_ext_audio)) {
		return FILE_TYPE_SOUND;
	}
	return 0;
}

static int file_extension_type(const char *dir, const char *relname)
{
	char path[FILE_MAX];
	BLI_join_dirfile(path, sizeof(path), dir, relname);
	return path_extension_type(path);
}

int ED_file_extension_icon(const char *path)
{
	int type = path_extension_type(path);
	
	if (type == FILE_TYPE_BLENDER)
		return ICON_FILE_BLEND;
	else if (type == FILE_TYPE_BLENDER_BACKUP)
		return ICON_FILE_BACKUP;
	else if (type == FILE_TYPE_IMAGE)
		return ICON_FILE_IMAGE;
	else if (type == FILE_TYPE_MOVIE)
		return ICON_FILE_MOVIE;
	else if (type == FILE_TYPE_PYSCRIPT)
		return ICON_FILE_SCRIPT;
	else if (type == FILE_TYPE_SOUND)
		return ICON_FILE_SOUND;
	else if (type == FILE_TYPE_FTFONT)
		return ICON_FILE_FONT;
	else if (type == FILE_TYPE_BTX)
		return ICON_FILE_BLANK;
	else if (type == FILE_TYPE_COLLADA)
		return ICON_FILE_BLANK;
	else if (type == FILE_TYPE_TEXT)
		return ICON_FILE_TEXT;
	
	return ICON_FILE_BLANK;
}

static void filelist_setfiletypes(struct FileList *filelist)
{
	struct direntry *file;
	int num;
	
	file = filelist->filelist;
	
	for (num = 0; num < filelist->numfiles; num++, file++) {
		file->type = file->s.st_mode;  /* restore the mess below */
#ifndef __APPLE__
		/* Don't check extensions for directories, allow in OSX cause bundles have extensions*/
		if (file->type & S_IFDIR) {
			continue;
		}
#endif
		file->flags = file_extension_type(filelist->dir, file->relname);
		
		if (filelist->filter_data.filter_glob[0] &&
		    BLI_testextensie_glob(file->relname, filelist->filter_data.filter_glob))
		{
			file->flags = FILE_TYPE_OPERATOR;
		}
	}
}

static void filelist_read_dir(struct FileList *filelist)
{
	if (!filelist) return;

	filelist->fidx = NULL;
	filelist->filelist = NULL;

	BLI_make_exist(filelist->dir);
	BLI_cleanup_dir(G.main->name, filelist->dir);
	filelist->numfiles = BLI_filelist_dir_contents(filelist->dir, &(filelist->filelist));

	/* We shall *never* get an empty list here, since we now the dir exists and is readable
	 * (ensured by BLI_make_exist()). So we expect at the very least the parent '..' entry. */
	BLI_assert(filelist->numfiles != 0);

	filelist_setfiletypes(filelist);
}

static void filelist_read_main(struct FileList *filelist)
{
	if (!filelist) return;
	filelist_from_main(filelist);
}

static void filelist_read_library(struct FileList *filelist)
{
	if (!filelist) return;
	BLI_cleanup_dir(G.main->name, filelist->dir);
	filelist_from_library(filelist);
	if (!filelist->libfiledata) {
		int num;
		struct direntry *file;

		filelist_read_dir(filelist);
		file = filelist->filelist;
		for (num = 0; num < filelist->numfiles; num++, file++) {
			if (BLO_has_bfile_extension(file->relname)) {
				char name[FILE_MAX];

				BLI_join_dirfile(name, sizeof(name), filelist->dir, file->relname);

				/* prevent current file being used as acceptable dir */
				if (BLI_path_cmp(G.main->name, name) != 0) {
					file->type &= ~S_IFMT;
					file->type |= S_IFDIR;
				}
			}
		}
	}
}

void filelist_readdir(struct FileList *filelist)
{
	filelist->readf(filelist);

	filelist->need_sorting = true;
	filelist->need_thumbnails = true;
	filelist_filter_clear(filelist);
}

int filelist_empty(struct FileList *filelist)
{
	return filelist->filelist == NULL;
}

void filelist_select_file(struct FileList *filelist, int index, FileSelType select, unsigned int flag, FileCheckType check)
{
	struct direntry *file = filelist_file(filelist, index);
	if (file != NULL) {
		int check_ok = 0; 
		switch (check) {
			case CHECK_DIRS:
				check_ok = S_ISDIR(file->type);
				break;
			case CHECK_ALL:
				check_ok = 1;
				break;
			case CHECK_FILES:
			default:
				check_ok = !S_ISDIR(file->type);
				break;
		}
		if (check_ok) {
			switch (select) {
				case FILE_SEL_REMOVE:
					file->selflag &= ~flag;
					break;
				case FILE_SEL_ADD:
					file->selflag |= flag;
					break;
				case FILE_SEL_TOGGLE:
					file->selflag ^= flag;
					break;
			}
		}
	}
}

void filelist_select(struct FileList *filelist, FileSelection *sel, FileSelType select, unsigned int flag, FileCheckType check)
{
	/* select all valid files between first and last indicated */
	if ((sel->first >= 0) && (sel->first < filelist->numfiltered) && (sel->last >= 0) && (sel->last < filelist->numfiltered)) {
		int current_file;
		for (current_file = sel->first; current_file <= sel->last; current_file++) {
			filelist_select_file(filelist, current_file, select, flag, check);
		}
	}
}

bool filelist_is_selected(struct FileList *filelist, int index, FileCheckType check)
{
	struct direntry *file = filelist_file(filelist, index);
	if (!file) {
		return 0;
	}
	switch (check) {
		case CHECK_DIRS:
			return S_ISDIR(file->type) && (file->selflag & FILE_SEL_SELECTED);
		case CHECK_FILES:
			return S_ISREG(file->type) && (file->selflag & FILE_SEL_SELECTED);
		case CHECK_ALL:
		default:
			return (file->selflag & FILE_SEL_SELECTED) != 0;
	}
}


bool filelist_islibrary(struct FileList *filelist, char *dir, char *group)
{
	return BLO_is_a_library(filelist->dir, dir, group);
}

static int groupname_to_code(const char *group)
{
	char buf[BLO_GROUP_MAX];
	char *lslash;
	
	BLI_strncpy(buf, group, sizeof(buf));
	lslash = (char *)BLI_last_slash(buf);
	if (lslash)
		lslash[0] = '\0';

	return buf[0] ? BKE_idcode_from_name(buf) : 0;
}

static void filelist_from_library(struct FileList *filelist)
{
	LinkNode *l, *names, *previews;
	struct ImBuf *ima;
	int ok, i, nprevs, nnames, idcode;
	char filename[FILE_MAX];
	char dir[FILE_MAX], group[BLO_GROUP_MAX];
	
	/* name test */
	ok = filelist_islibrary(filelist, dir, group);
	if (!ok) {
		/* free */
		if (filelist->libfiledata) BLO_blendhandle_close(filelist->libfiledata);
		filelist->libfiledata = NULL;
		return;
	}
	
	BLI_strncpy(filename, G.main->name, sizeof(filename));

	/* there we go */
	/* for the time being only read filedata when libfiledata==0 */
	if (filelist->libfiledata == NULL) {
		filelist->libfiledata = BLO_blendhandle_from_file(dir, NULL);
		if (filelist->libfiledata == NULL) return;
	}
	
	idcode = groupname_to_code(group);

	/* memory for strings is passed into filelist[i].relname
	 * and freed in freefilelist */
	if (idcode) {
		previews = BLO_blendhandle_get_previews(filelist->libfiledata, idcode, &nprevs);
		names = BLO_blendhandle_get_datablock_names(filelist->libfiledata, idcode, &nnames);
		/* ugh, no rewind, need to reopen */
		BLO_blendhandle_close(filelist->libfiledata);
		filelist->libfiledata = BLO_blendhandle_from_file(dir, NULL);
		
	}
	else {
		previews = NULL;
		nprevs = 0;
		names = BLO_blendhandle_get_linkable_groups(filelist->libfiledata);
		nnames = BLI_linklist_length(names);
	}

	filelist->numfiles = nnames + 1;
	filelist->filelist = malloc(filelist->numfiles * sizeof(*filelist->filelist));
	memset(filelist->filelist, 0, filelist->numfiles * sizeof(*filelist->filelist));

	filelist->filelist[0].relname = BLI_strdup("..");
	filelist->filelist[0].type |= S_IFDIR;
		
	for (i = 0, l = names; i < nnames; i++, l = l->next) {
		const char *blockname = l->link;

		filelist->filelist[i + 1].relname = BLI_strdup(blockname);
		if (idcode) {
			filelist->filelist[i + 1].type |= S_IFREG;
		}
		else {
			filelist->filelist[i + 1].type |= S_IFDIR;
		}
	}
	
	if (previews && (nnames != nprevs)) {
		printf("filelist_from_library: error, found %d items, %d previews\n", nnames, nprevs);
	}
	else if (previews) {
		for (i = 0, l = previews; i < nnames; i++, l = l->next) {
			PreviewImage *img = l->link;
			
			if (img) {
				unsigned int w = img->w[ICON_SIZE_PREVIEW];
				unsigned int h = img->h[ICON_SIZE_PREVIEW];
				unsigned int *rect = img->rect[ICON_SIZE_PREVIEW];

				/* first allocate imbuf for copying preview into it */
				if (w > 0 && h > 0 && rect) {
					ima = IMB_allocImBuf(w, h, 32, IB_rect);
					memcpy(ima->rect, rect, w * h * sizeof(unsigned int));
					filelist->filelist[i + 1].image = ima;
					filelist->filelist[i + 1].flags = FILE_TYPE_IMAGE;
				}
			}
		}
	}

	BLI_linklist_free(names, free);
	if (previews) BLI_linklist_free(previews, BKE_previewimg_freefunc);

	BLI_strncpy(G.main->name, filename, sizeof(filename));  /* prevent G.main->name to change */
}

static void filelist_from_main(struct FileList *filelist)
{
	ID *id;
	struct direntry *files, *firstlib = NULL;
	ListBase *lb;
	int a, fake, idcode, ok, totlib, totbl;
	
	// filelist->type = FILE_MAIN; // XXXXX TODO: add modes to filebrowser

	if (filelist->dir[0] == '/') filelist->dir[0] = 0;
	
	if (filelist->dir[0]) {
		idcode = groupname_to_code(filelist->dir);
		if (idcode == 0) filelist->dir[0] = 0;
	}
	
	if (filelist->dir[0] == 0) {
		
		/* make directories */
#ifdef WITH_FREESTYLE
		filelist->numfiles = 24;
#else
		filelist->numfiles = 23;
#endif
		filelist->filelist = (struct direntry *)malloc(filelist->numfiles * sizeof(struct direntry));
		
		for (a = 0; a < filelist->numfiles; a++) {
			memset(&(filelist->filelist[a]), 0, sizeof(struct direntry));
			filelist->filelist[a].type |= S_IFDIR;
		}
		
		filelist->filelist[0].relname = BLI_strdup("..");
		filelist->filelist[1].relname = BLI_strdup("Scene");
		filelist->filelist[2].relname = BLI_strdup("Object");
		filelist->filelist[3].relname = BLI_strdup("Mesh");
		filelist->filelist[4].relname = BLI_strdup("Curve");
		filelist->filelist[5].relname = BLI_strdup("Metaball");
		filelist->filelist[6].relname = BLI_strdup("Material");
		filelist->filelist[7].relname = BLI_strdup("Texture");
		filelist->filelist[8].relname = BLI_strdup("Image");
		filelist->filelist[9].relname = BLI_strdup("Ika");
		filelist->filelist[10].relname = BLI_strdup("Wave");
		filelist->filelist[11].relname = BLI_strdup("Lattice");
		filelist->filelist[12].relname = BLI_strdup("Lamp");
		filelist->filelist[13].relname = BLI_strdup("Camera");
		filelist->filelist[14].relname = BLI_strdup("Ipo");
		filelist->filelist[15].relname = BLI_strdup("World");
		filelist->filelist[16].relname = BLI_strdup("Screen");
		filelist->filelist[17].relname = BLI_strdup("VFont");
		filelist->filelist[18].relname = BLI_strdup("Text");
		filelist->filelist[19].relname = BLI_strdup("Armature");
		filelist->filelist[20].relname = BLI_strdup("Action");
		filelist->filelist[21].relname = BLI_strdup("NodeTree");
		filelist->filelist[22].relname = BLI_strdup("Speaker");
#ifdef WITH_FREESTYLE
		filelist->filelist[23].relname = BLI_strdup("FreestyleLineStyle");
#endif
	}
	else {

		/* make files */
		idcode = groupname_to_code(filelist->dir);
		
		lb = which_libbase(G.main, idcode);
		if (lb == NULL) return;
		
		id = lb->first;
		filelist->numfiles = 0;
		while (id) {
			if (!filelist->filter_data.hide_dot || id->name[2] != '.') {
				filelist->numfiles++;
			}
			
			id = id->next;
		}
		
		/* XXXXX TODO: if databrowse F4 or append/link filelist->hide_parent has to be set */
		if (!filelist->filter_data.hide_parent) filelist->numfiles += 1;
		filelist->filelist = filelist->numfiles > 0 ? (struct direntry *)malloc(filelist->numfiles * sizeof(struct direntry)) : NULL;

		files = filelist->filelist;
		
		if (!filelist->filter_data.hide_parent) {
			memset(&(filelist->filelist[0]), 0, sizeof(struct direntry));
			filelist->filelist[0].relname = BLI_strdup("..");
			filelist->filelist[0].type |= S_IFDIR;
		
			files++;
		}
		
		id = lb->first;
		totlib = totbl = 0;
		
		while (id) {
			ok = 1;
			if (ok) {
				if (!filelist->filter_data.hide_dot || id->name[2] != '.') {
					memset(files, 0, sizeof(struct direntry));
					if (id->lib == NULL) {
						files->relname = BLI_strdup(id->name + 2);
					}
					else {
						files->relname = MEM_mallocN(FILE_MAX + (MAX_ID_NAME - 2),     "filename for lib");
						BLI_snprintf(files->relname, FILE_MAX + (MAX_ID_NAME - 2) + 3, "%s | %s", id->lib->name, id->name + 2);
					}
					files->type |= S_IFREG;
#if 0               /* XXXXX TODO show the selection status of the objects */
					if (!filelist->has_func) { /* F4 DATA BROWSE */
						if (idcode == ID_OB) {
							if ( ((Object *)id)->flag & SELECT) files->selflag |= FILE_SEL_SELECTED;
						}
						else if (idcode == ID_SCE) {
							if ( ((Scene *)id)->r.scemode & R_BG_RENDER) files->selflag |= FILE_SEL_SELECTED;
						}
					}
#endif
					files->nr = totbl + 1;
					files->poin = id;
					fake = id->flag & LIB_FAKEUSER;
					if (idcode == ID_MA || idcode == ID_TE || idcode == ID_LA || idcode == ID_WO || idcode == ID_IM) {
						files->flags |= FILE_TYPE_IMAGE;
					}
					if      (id->lib && fake) BLI_snprintf(files->extra, sizeof(files->extra), "LF %d",    id->us);
					else if (id->lib)         BLI_snprintf(files->extra, sizeof(files->extra), "L    %d",  id->us);
					else if (fake)            BLI_snprintf(files->extra, sizeof(files->extra), "F    %d",  id->us);
					else                      BLI_snprintf(files->extra, sizeof(files->extra), "      %d", id->us);
					
					if (id->lib) {
						if (totlib == 0) firstlib = files;
						totlib++;
					}
					
					files++;
				}
				totbl++;
			}
			
			id = id->next;
		}
		
		/* only qsort of library blocks */
		if (totlib > 1) {
			qsort(firstlib, totlib, sizeof(struct direntry), compare_name);
		}
	}
}

/* ********** Thumbnails job ********** */

typedef struct ThumbnailJob {
	ListBase loadimages;
	ImBuf *static_icons_buffers[BIFICONID_LAST];
	const short *stop;
	const short *do_update;
	struct FileList *filelist;
	ReportList reports;
} ThumbnailJob;

bool filelist_need_thumbnails(FileList *filelist)
{
	return filelist->need_thumbnails;
}

static void thumbnail_joblist_free(ThumbnailJob *tj)
{
	FileImage *limg = tj->loadimages.first;
	
	/* free the images not yet copied to the filelist -> these will get freed with the filelist */
	for (; limg; limg = limg->next) {
		if ((limg->img) && (!limg->done)) {
			IMB_freeImBuf(limg->img);
		}
	}
	BLI_freelistN(&tj->loadimages);
}

static void thumbnails_startjob(void *tjv, short *stop, short *do_update, float *UNUSED(progress))
{
	ThumbnailJob *tj = tjv;
	FileImage *limg = tj->loadimages.first;

	tj->stop = stop;
	tj->do_update = do_update;

	while ((*stop == 0) && (limg)) {
		if (limg->flags & FILE_TYPE_IMAGE) {
			limg->img = IMB_thumb_manage(limg->path, THB_NORMAL, THB_SOURCE_IMAGE);
		}
		else if (limg->flags & (FILE_TYPE_BLENDER | FILE_TYPE_BLENDER_BACKUP)) {
			limg->img = IMB_thumb_manage(limg->path, THB_NORMAL, THB_SOURCE_BLEND);
		}
		else if (limg->flags & FILE_TYPE_MOVIE) {
			limg->img = IMB_thumb_manage(limg->path, THB_NORMAL, THB_SOURCE_MOVIE);
			if (!limg->img) {
				/* remember that file can't be loaded via IMB_open_anim */
				limg->flags &= ~FILE_TYPE_MOVIE;
				limg->flags |= FILE_TYPE_MOVIE_ICON;
			}
		}
		*do_update = true;
		PIL_sleep_ms(10);
		limg = limg->next;
	}
}

static void thumbnails_update(void *tjv)
{
	ThumbnailJob *tj = tjv;

	if (tj->filelist && tj->filelist->filelist) {
		FileImage *limg = tj->loadimages.first;
		while (limg) {
			if (!limg->done && limg->img) {
				tj->filelist->filelist[limg->index].image = limg->img;
				/* update flag for movie files where thumbnail can't be created */
				if (limg->flags & FILE_TYPE_MOVIE_ICON) {
					tj->filelist->filelist[limg->index].flags &= ~FILE_TYPE_MOVIE;
					tj->filelist->filelist[limg->index].flags |= FILE_TYPE_MOVIE_ICON;
				}
				limg->done = true;
			}
			limg = limg->next;
		}
	}
}

static void thumbnails_endjob(void *tjv)
{
	ThumbnailJob *tj = tjv;

	if (!*tj->stop) {
		tj->filelist->need_thumbnails = false;
	}
}

static void thumbnails_free(void *tjv)
{
	ThumbnailJob *tj = tjv;
	thumbnail_joblist_free(tj);
	MEM_freeN(tj);
}


void thumbnails_start(FileList *filelist, const bContext *C)
{
	wmJob *wm_job;
	ThumbnailJob *tj;
	int idx;
	
	/* prepare job data */
	tj = MEM_callocN(sizeof(ThumbnailJob), "thumbnails\n");
	tj->filelist = filelist;
	for (idx = 0; idx < filelist->numfiles; idx++) {
		if (!filelist->filelist[idx].image) {
			if (filelist->filelist[idx].flags & (FILE_TYPE_IMAGE | FILE_TYPE_MOVIE |
			                                     FILE_TYPE_BLENDER | FILE_TYPE_BLENDER_BACKUP))
			{
				FileImage *limg = MEM_callocN(sizeof(FileImage), "loadimage");
				BLI_strncpy(limg->path, filelist->filelist[idx].path, FILE_MAX);
				limg->index = idx;
				limg->flags = filelist->filelist[idx].flags;
				BLI_addtail(&tj->loadimages, limg);
			}
		}
	}

	BKE_reports_init(&tj->reports, RPT_PRINT);

	/* setup job */
	wm_job = WM_jobs_get(CTX_wm_manager(C), CTX_wm_window(C), filelist, "Thumbnails",
	                     0, WM_JOB_TYPE_FILESEL_THUMBNAIL);
	WM_jobs_customdata_set(wm_job, tj, thumbnails_free);
	WM_jobs_timer(wm_job, 0.5, NC_WINDOW, NC_WINDOW);
	WM_jobs_callbacks(wm_job, thumbnails_startjob, NULL, thumbnails_update, thumbnails_endjob);

	/* start the job */
	WM_jobs_start(CTX_wm_manager(C), wm_job);
}

void thumbnails_stop(wmWindowManager *wm, FileList *filelist)
{
	WM_jobs_kill_type(wm, filelist, WM_JOB_TYPE_FILESEL_THUMBNAIL);
}

int thumbnails_running(wmWindowManager *wm, FileList *filelist)
{
	return WM_jobs_test(wm, filelist, WM_JOB_TYPE_FILESEL_THUMBNAIL);
}
